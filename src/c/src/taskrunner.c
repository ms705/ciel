/*
 ============================================================================
 Name        : rcce-taskrunner.c
 Author      : Malte Schwarzkopf
 Version     :
 Copyright   : (c) 2011 Malte Schwarzkopf
 Description :
 ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <strings.h>
#include <stdint.h>

#include "taskrunner.h"

//int num_ranks, remote_rank, my_rank;
#ifdef RCCE
iRCCE_WAIT_LIST general_waitlist;

iRCCE_RECV_REQUEST *recv_requests;
iRCCE_SEND_REQUEST *send_requests;
#endif


int s; 			// socket descriptor
FILE *sockfd;	// socket FD


void tr_init(int argc, char **argv) {

#ifdef RCCE

	printf("RCCE enabled\n");

	RCCE_init(&argc, &argv);
	iRCCE_init();

	iRCCE_init_wait_list(&general_waitlist);

#else

    struct sockaddr_un saun;
    register int len;

    // Get a streaming UNIX domain socket
    if ((s = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
    	perror("socket creation error");
    	exit(1);
    }

    // Create the address to connect to
    saun.sun_family = AF_UNIX;
    strcpy(saun.sun_path, SOCK_ADDR);

    len = sizeof(saun.sun_family) + strlen(saun.sun_path);

    if (connect(s, &saun, len) < 0) {
    	perror("failed to connect to socket");
    	exit(1);
    }

    sockfd = fdopen(s, "r");

    printf("task runner sockets set up\n");

#endif

}


void tr_send(void) {

	char c[14];
	int len = sizeof(c);
	bzero(c, len);

	sprintf(c, "Hello world!\n");

	SEND((char *)&len, len, s);
	SEND_B(c, len, s);

}


// send_message()

// wait_for_receive() ?

// start_exec()


void tr_hello(void) {

	printf("Hello from the RCCE task runner!\n");

}
