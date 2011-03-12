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

#define COORD_ADDR "libciel-scc-core0"

void sock_set_id(uint8_t id);

int sock_init_server(int *sock, uint8_t blocking);

int sock_init_client(int *sock);

void sock_set_nonblock(int);

void sock_send(int, char *, size_t);

int sock_recv(int sockfd, char *buf, unsigned int len);

void copy_data(int, int);

static char * get_remote_addr(uint8_t id);

#endif /* SOCKCOMMON_H */


