EXTERNAL=../../../ext
RCCEROOT=$(EXTERNAL)/rcce
IRCCEROOT=$(EXTERNAL)/iRCCE

#SYMBOLSPATH=$(RCCEROOT)/common/symbols.in
#include $(SYMBOLSPATH)

ENABLE_RCCE = 0

ARCHIVE := $(RCCEROOT)/bin/SCC_LINUX/libRCCE_bigflags_nongory_nopwrmgmt.a

CCOMPILE := gcc
CCFLAGS := -O3 -DSOCK_UNIX
INCLUDES := -I$(RCCEROOT)/include -I$(IRCCEROOT)/include

ifeq ($(ENABLE_RCCE),1)
	DEF := -DRCCE
#	CCFLAGS := $(CCFLAGS) -m32
	LIBCIELOBJS := taskrunner.o coordinator.o   $(ARCHIVE)
else
	LIBCIELOBJS := taskrunner.o coordinator.o sock-common.o  $(ARCHIVE)
endif 


default: loader libciel.so

all: loader streamfs libciel-scc libciel.so

loader: loader.c
	$(CCOMPILE) -std=gnu99 -o loader -I../include -ldl loader.c

streamfs: streamfs.c
	$(CCOMPILE) -Wall -Werror -D_FILE_OFFSET_BITS=64 -o streamfs streamfs.c -lfuse -lpthread

libciel.o: libciel.c
	$(CCOMPILE) libciel.c -std=gnu99 -c -o libciel.o -D_FILE_OFFSET_BITS=64 -fPIC -I../../../ext/jansson-install/include

libciel.so: libciel.o
	$(CCOMPILE) libciel.o -o libciel.so -shared -Wl,-rpath,'$$ORIGIN/../../../ext/jansson-install/lib' -L../../../ext/jansson-install/lib -ljansson

%.o: %.c
	$(CCOMPILE) $(CCFLAGS) -fPIC -g -c -Wall $(INCLUDES) $(DEF) $<

libciel-scc: $(LIBCIELOBJS)
	$(CCOMPILE) $(CCFLAGS) -shared -Wl,-soname=ciel-scc.so -o libciel-scc.so $(LIBCIELOBJS)

clean:
	-rm *.o *.so loader streamfs
