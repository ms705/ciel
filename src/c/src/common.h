/*
 * common.h
 *
 *  Created on: 9 Mar 2011
 *      Author: ms705
 */


#ifdef RCCE

#define SEND(B, L, D) iRCCE_isend((B), (L), (D), send_requests)
#define RECV(B, L, S) iRCCE_irecv((B), (L), (S), recv_requests)

#else

#define SEND(B, L, D) sock_send((D), (B), (L))
#define RECV(B, L, S) sock_recv((S), (B), (L))

#endif



#ifdef RCCE

#include "RCCE.h"
#include "iRCCE.h"

// The master core ID -- TODO: this shouldn't be hardcoded
#define MASTER 0

#else

// we'll fake out RCCE using sockets
#include "sock-common.h"

#define MASTER "libciel-scc-socket"

#endif


#if 0
/**
 * Stub main function in case anyone ever tries to run this directly.
 */
int main(int argc, char **argv) {

	// This shouldn't usually be called
	printf("Use libciel-scc as a shared library; it cannot be run directly. Exiting.\n");

	return EXIT_SUCCESS;

}
#endif
