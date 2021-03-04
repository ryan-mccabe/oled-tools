# filecache

VERSION=1.0
DATE=02 Sep 2020

# Honour the environment variable CC
CC	= gcc

LIBMAKEDUMPFILE_PATH167=../libcore/makedumpfile_1.6.7
LIBMAKEDUMPFILE_PATH157=../libcore/makedumpfile_1.5.7
CFLAGS_BASE := $(CFLAGS) -g -O2 -Wall -D_FILE_OFFSET_BITS=64 \
		-D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE
CFLAGS      := $(CFLAGS_BASE) -DVERSION='"$(VERSION)"' -DRELEASE_DATE='"$(DATE)"'

SRC_PART_FILECACHE = filecache.c lib.c
SRC_PART_DENTRYCACHE = dentrycache.c lib.c

LIBS = -ldw -ldl -lelf -lz -lbz2
LIBS := -lpthread $(LIBS)

try-run = $(shell set -e;		\
	TMP=".$$$$.tmp";		\
	if ($(1)) >/dev/null 2>&1;	\
	then echo "$(2)";		\
	else echo "$(3)";		\
	fi;				\
	rm -f "$$TMP")

LINK_TEST_PROG="int clock_gettime(); int main(){ return clock_gettime(); }"
LIBS := $(LIBS) $(call try-run,\
	echo $(LINK_TEST_PROG) | $(CC) $(CFLAGS) -o "$$TMP" -x c -,,-lrt)

# elfutils-0.178 or later does not install libebl.a.
LINK_TEST_PROG="int main() { return 0; }"
LIBS := $(LIBS) $(call try-run,\
	echo $(LINK_TEST_PROG) | $(CC) -o "$$TMP" -x c - -lebl,-lebl,)

all: filecache filecache_uek4 dentrycache dentrycache_uek4

filecache:
	rm -f filecache.o
	$(CC) $(CFLAGS) -DKASLR -I${LIBMAKEDUMPFILE_PATH167} -L${LIBMAKEDUMPFILE_PATH167} $(SRC_PART_FILECACHE) $(LDFLAGS) -rdynamic -o $@ -lcore $< $(LIBS)

filecache_uek4:
	rm -f filecache.o
	$(CC) $(CFLAGS) -I${LIBMAKEDUMPFILE_PATH157} -L${LIBMAKEDUMPFILE_PATH157} $(SRC_PART_FILECACHE) $(LDFLAGS) -rdynamic -o $@ -lcore $< $(LIBS)

dentrycache:
	rm -f dentrycache.o
	$(CC) $(CFLAGS) -DKASLR -I${LIBMAKEDUMPFILE_PATH167} -L${LIBMAKEDUMPFILE_PATH167} $(SRC_PART_DENTRYCACHE) $(LDFLAGS) -rdynamic -o $@ -lcore $< $(LIBS)

dentrycache_uek4:
	rm -f dentrycache.o
	$(CC) $(CFLAGS) -I${LIBMAKEDUMPFILE_PATH157} -L${LIBMAKEDUMPFILE_PATH157} $(SRC_PART_DENTRYCACHE) $(LDFLAGS) -rdynamic -o $@ -lcore $< $(LIBS)

clean:
	rm -f $(OBJ_PART) $(OBJ_ARCH) filecache filecache_uek4 dentrycache dentrycache_uek4 filecache.o dentrycache.o lib.o
