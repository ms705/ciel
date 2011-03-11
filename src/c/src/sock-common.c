
#include "sock-common.h"

void sock_send(int sockfd, char *data, size_t len) {

	send(sockfd, data, len, 0);

}


void sock_set_nonblock(int socket) {
	int flags;
	flags = fcntl(socket,F_GETFL,0);
	assert(flags != -1);
	fcntl(socket, F_SETFL, flags | O_NONBLOCK);
}


void copy_data(int srcFD, int destFD) {

	char buf[1024];
	int count;
	while ((count=read(srcFD, buf, sizeof(buf)))>0) {

		if (write(destFD, buf, count)!=count) {
			perror("write");
			exit(1);
		}
	}

	if (count<0) {
		perror("read");
		exit(1);
	}

}

