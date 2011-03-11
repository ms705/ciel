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
#endif


int s; 			// socket descriptor
FILE *sockfd;	// socket FD
struct sockaddr_un saun;
struct sockaddr_un from_saun;
socklen_t from_len;

#define FD_STDOUT 1

void coord_init() {

#ifdef RCCE

	int argc;
	char **argv;

	printf("RCCE enabled\n");

	RCCE_init(&argc, &argv);
    iRCCE_init();

    iRCCE_init_wait_list(&general_waitlist);

#else

    if(coord_sock_init() > 1) {
    	perror("Failed to set up socket, exiting");
    	exit(1);
    }

    printf("coordinator sockets set up\n");

#endif

}


int coord_sock_init() {

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


void coord_read() {

    char buf[1024];
    int rval, i;

    int msgsock = accept(s, (const struct sockaddr *)&from_saun, &from_len);
    if (msgsock == -1)
            //perror("accept failed");
			return;
    else do {
            memset(buf, 0, sizeof(buf));
            if ((rval  = read(msgsock, buf,  1024)) < 0)
                    perror("reading stream message");
            i = 0;
            if (rval == 0)
                    printf("Ending connection\n");
            else
                    printf("-->%s\n", buf);
    } while (rval != 0);
    close(msgsock);

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
