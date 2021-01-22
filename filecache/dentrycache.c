#include <limits.h>
#include "makedumpfile.h"
#include "elf_info.h"
#include "print_info.h"
#include "lib.h"

const char *version_str = "1.1";
/* version history:
 * 1.0	-- the first version
 * 1.1  -- fix dentry hash walking
 * 1.1  -- no-limit support
 */

/*
 * kaslr_off: the offset for kaslr.
 */
int dentrycache_dump(int limit, int negative_only,
		     unsigned long long *r_addresses)
{
	unsigned long long dentry_hashtable = r_addresses[0];
	unsigned long long d_hash_shift = r_addresses[1];
	unsigned long max_idx, i, addr, next, dentry_addr, inode;
	unsigned int d_hash_shift_val, file_idx = 0;
	char *path;

	MSG("dentrycache, limit=%d negative_only=%d\n", limit, negative_only);
	MSG("kernel version: %s\n", info->release);
	MSG("dentrycache version: %s\n", version_str);
	if (!is_supported_kernel())
		return -1;

	if (limit == 0)
		limit = INT_MAX;
	hardcode_offsets();

	dentry_hashtable = read_pointer(dentry_hashtable, "dentry_hashtable");
	if (0 == dentry_hashtable) {
		ERRMSG("Invalid address of dentry_hashtable passed in\n");
		return -1;
	}
	d_hash_shift_val = read_unsigned(d_hash_shift);
	if (0 == d_hash_shift_val) {
		ERRMSG("Invalid address of d_hash_shift passed in\n");
		return -1;
	}

	max_idx = 1 << d_hash_shift_val;

	MSG("Listing dentry path:\n");
	MSG("-------------------------------------------------------------\n");
	for (i = 0; i < max_idx; i++) {
		addr = dentry_hashtable +  i * sizeof(void *);

		/* hlist_bl_head->first */
		addr += OFFSET(hlist_bl_head.first);
		addr = read_pointer(addr, "hlist_bl_node");
		if (!addr)
			continue;

		do {
			next = read_pointer(addr + OFFSET(hlist_bl_node.next),
					    "hlist_bl_node.next");	
			dentry_addr = addr - OFFSET(dentry.d_hash);
			path = dentry_path(dentry_addr);
			inode = read_pointer(dentry_addr + OFFSET(dentry.d_inode), "dentru.d_inode");
			if (negative_only && inode)
				continue;

			if (inode)
				MSG("%08d %s\n", ++file_idx, path);
			else
				MSG("%08d %s (negative)\n", ++file_idx, path);

			if (file_idx >= limit)
				break;
		} while ((addr = next));

		if (file_idx >= limit)
			break;
	}

	return 0;
}

static void show_help()
{
	MSG("dentrycache is a tool that dumps the dentry path on live systems.\n");
	MSG("Output is one dentry per line.\n");
	MSG("Use --limit option to sepecify the max number of dentries to list\n");
	MSG("Use --negative option to output negative dentries only\n");
	MSG("Use -kexec option when run in kexec mode, look at the panicked production kernel");
	MSG ("rather than current running kernel\n");
	MSG("parameters and options:\n");
	MSG("   -l, --limit <number>       list at most <number> dentries, 0 for no limit, 10000 by default\n");
	MSG("   -n, --negative             list negative dentries only, disabled by default\n");
	MSG("   -k, --kexec                run in kexec mode\n");
	MSG("   -h, --help                 show this information\n");
	MSG("   -V, --version              show version\n");
	MSG("\n");
	MSG("Note: works on Oracle UEK4/UEK5/UEK6 kernels only\n");
	MSG("\n");
}

static struct option longopts[] = {
	{"limit", required_argument, NULL, 'l'},
	{"negative", no_argument, NULL, 'n'},
	{"help", no_argument, NULL, 'h'},
	{"version", no_argument, NULL, 'V'},
	{"kexec", no_argument, NULL, 'k'},
	{0, 0, 0, 0}
};

static char *shortopts = "l:nhVk";

int
main(int argc, char *argv[])
{
#define NR_SYM 2
	int opt, limit = 10000, negative_only = 0, i, help = 0, version = 0;
	// symbols to look for
	char *sym_names[] = {"dentry_hashtable", "d_hash_shift"};
	// randomized addresses
	unsigned long long r_addresses[NR_SYM];
	// original addresses
	unsigned long long o_addresses[NR_SYM];
	char *real_args[12];
	int kexec_mode = 0;
	int core_idx;
	int ret = -1;
	uid_t uid;

	message_level = DEFAULT_MSG_LEVEL;
	if (argc > 8) {
		MSG("Commandline parameter is invalid.\n");
		return -1;
	}

	/* user check, root only */
	uid = getuid();
	if (uid != 0) {
		MSG("run as root only.\n");
		return -1;
	}

	for (i = 0; i < argc; i++)
		real_args[i] = argv[i];

	core_idx = i;
	real_args[i++] = "/proc/kcore";
	real_args[i] = "x";
	argc += 2;

	while ((opt = getopt_long(argc, real_args, shortopts, longopts,
	    NULL)) != -1) {
		switch (opt) {
		case 'l':
			limit = atoi(optarg);
			break;
		case 'n':
			negative_only = 1;
			break;
		case 'h':
			help = 1;
			break;
		case 'V':
			version = 1;
			break;
		case 'k':
			kexec_mode = 1;
			break;

		case '?':
			MSG("Commandline parameter is invalid.\n");
			MSG("Try `filecache --help' for more information.\n");
			goto out;
		}
	}

	if (help) {
		show_help();
		return 0;
	}

	if (version) {
		MSG("dentrycache version: %s\n", version_str);
		return 0;
	}

	if (!init_core(argc, real_args, 0))
		goto out;

#ifdef KASLR
	if (!find_kaslr_offsets()) {
		ERRMSG("find_kaslr_offsets failed\n");
		goto out;
	}
#endif
	/* get the randomized addresses and the original ones for kcore */
	symbol_addresses(NR_SYM, sym_names, r_addresses, o_addresses);
	for (i = 0; i < NR_SYM; i++) {
		if (r_addresses[i] == 0) {
			ERRMSG("failed to get address for %s\n", sym_names[i]);
			goto out;
		}
	}

	if (kexec_mode) {
		MSG("Running in kexec mode.\n");

		real_args[core_idx] = "/proc/vmcore";

		// relealse info for /proc/kcore
		free_info(info);

		// and rework with /proc/vmcore
		if (!init_core(argc, real_args, 1))
			goto out;
#ifdef KASLR
		if (!find_kaslr_offsets()) {
			ERRMSG("find_kaslr_offsets failed\n");
			goto out;
		}
		for (i = 0; i < NR_SYM; i++) {
			r_addresses[i] = o_addresses[i] + info->kaslr_offset;
		}
#endif
	}

	ret = dentrycache_dump(limit, negative_only, r_addresses);
out:
	MSG("\n");
	free_info(info);
	return ret;
}
