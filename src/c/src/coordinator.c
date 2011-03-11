/*
 ============================================================================
 Name        : rcce-coordinator.c
 Author      : Malte Schwarzkopf
 Version     :
 Copyright   : (c) 2011 Malte Schwarzkopf
 Description :
 ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>

#include "coordinator.h"

//int num_ranks, remote_rank, my_rank;
#ifdef RCCE

iRCCE_WAIT_LIST general_waitlist;

iRCCE_RECV_REQUEST *recv_requests;
iRCCE_SEND_REQUEST *send_requests;

#else

int s; 			// socket descriptor
FILE *sockfd;	// socket FD
struct sockaddr_un saun;

#endif

#define FD_STDOUT 1

void coord_init(int argc, char **argv) {

	int i;

#ifdef RCCE

	printf("RCCE enabled\n");

	RCCE_init(&argc, &argv);
	printf("RCCE init done\n");

	iRCCE_init();
	printf("iRCCE init done\n");

    iRCCE_init_wait_list(&general_waitlist);
	printf("waitlist init done\n");

#else

    if(coord_sock_init() > 1) {
    	perror("Failed to set up socket, exiting");
    	exit(1);
    }

    printf("coordinator sockets set up\n");

#endif

    printf("init finished");

}

#ifndef RCCE
static int coord_sock_init() {

    register int len;

    // Get a streaming UNIX domain socket
    if ((s = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
    	perror("socket creation error");
    	return 1;
    }

    // Create the address to connect to
    saun.sun_family = AF_UNIX;
    strcpy(saun.sun_path, MASTER);

    // delete the socket file if it still exists
    unlink(MASTER);

    len = sizeof(saun.sun_family) + strlen(saun.sun_path);

    if (bind(s, (const struct sockaddr *)&saun, len) < 0) {
    	perror("failed to bind to socket");
    	return 1;
    }

    if (listen(s, 5) < 0) {
    	perror("failed to listen on socket");
    	return 1;
    }

    // Make the socket non-blocking
    sock_set_nonblock(s);

    return 0;
}
#endif


void coord_read() {

    char buf[1024];

#ifdef RCCE
    RECV(buf, sizeof(buf), 1); // XXX hardcoded remote rank
#else
    RECV(buf, sizeof(buf), s);
#endif

    printf(buf);

}

// send_message()

// wait_for_receive() ?

// start_exec()


void coord_quit() {

	printf("RCCE coordinator quitting\n");

#ifdef RCCE
#else
	// close the socket
	close(s);
#endif

	exit(0);

}

void coord_hello() {

	printf("Hello from the RCCE coordinator!\n");

}
