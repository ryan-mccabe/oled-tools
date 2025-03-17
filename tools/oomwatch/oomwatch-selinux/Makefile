IAM = pcp-oomwatch

default: all

all: $(IAM).pp

$(IAM).pp: $(IAM).te $(IAM).fc
	$(MAKE) -f /usr/share/selinux/devel/Makefile $(IAM).pp

clean:
	rm -f $(IAM).pp $(IAM).if $(IAM).bz2
	rm -rf tmp

install:
	bzip2 -f -9 $(IAM).pp
	install --mode=644 -D $(CURDIR)/$(IAM).pp.bz2 $(DESTDIR)/usr/share/selinux/packages/targeted/$(IAM).pp.bz2
	#@echo "run semodule -i"
	#semodule -X200 -s targeted -i /usr/share/selinux/packages/targeted/$(IAM).pp.bz2

uninstall:
	#@echo "run semodule -r"
	#semodule -X200 -r $(IAM)

