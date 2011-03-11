EXTERNAL=../../../ext
RCCEROOT=$(EXTERNAL)/rcce
IRCCEROOT=$(EXTERNAL)/iRCCE

#SYMBOLSPATH=$(RCCEROOT)/common/symbols.in
#include $(SYMBOLSPATH)

ENABLE_RCCE = 0

ARCHIVE := $(RCCEROOT)/bin/SCC_LINUX/libRCCE_bigflags_nongory_nopwrmgmt.a

CCOMPILE := gcc
CCFLAGS := -O3
INCLUDES := -I$(RCCEROOT)/include -I$(IRCCEROOT)/include

ifeq ($(ENABLE_RCCE),1)
	DEF := -DRCCE
	CCFLAGS := $(CCFLAGS) -m32
	LIBCIELOBJS := taskrunner.o coordinator.o   $(ARCHIVE)
else
	LIBCIELOBJS := taskrunner.o coordinator.o sock-common.o  $(ARCHIVE)
endif 


default:
	@echo "Usage: make loader  "
	@echo "       make streamfs  "
	@echo "       make libciel-scc "

all: loader streamfs libciel-scc

loader: loader.c
	$(CCOMPILE) -std=gnu99 -o loader -I../include -ldl loader.c

streamfs: streamfs.c
	$(CCOMPILE) -Wall -Werror -D_FILE_OFFSET_BITS=64 -o streamfs streamfs.c -lfuse -lpthread

%.o: %.c
	$(CCOMPILE) $(CCFLAGS) -fPIC -g -c -Wall $(INCLUDES) $(DEF) $<

libciel-scc: $(LIBCIELOBJS)
	$(CCOMPILE) $(CCFLAGS) -shared -Wl,-soname=ciel-scc.so -o libciel-scc.so $(LIBCIELOBJS)

clean: 
	@ rm -f *.o loader streamfs libciel-scc.so
