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

void sock_set_nonblock(int);

void sock_send(int, char *, size_t);


void copy_data(int, int);


#endif /* SOCKCOMMON_H */


