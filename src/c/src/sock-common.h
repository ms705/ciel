/*
 * sock-common.h
 *
 *  Created on: 9 Mar 2011
 *      Author: ms705
 */

#ifndef SOCKCOMMON_H
#define SOCKCOMMON_H

#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>
#include <assert.h>
#include <stdio.h>
#include <stdint.h>

#define SOCK_ADDR "libciel-scc-socket"

int sock_init(int *sock, uint8_t blocking);

void sock_set_nonblock(int);

void sock_send(int, char *, size_t);

int sock_recv(int sockfd, char *buf, unsigned int len);

void copy_data(int, int);


#endif /* SOCKCOMMON_H */


