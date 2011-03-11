
#include "sock-common.h"

void sock_send(int sockfd, char *data, size_t len) {

	send(sockfd, data, len, 0);

}

void sock_recv(int sockfd, char *buf, unsigned int len) {

	struct sockaddr_un from_saun;
	socklen_t from_len;
    int rval;

    int msgsock = accept(sockfd, (const struct sockaddr *)&from_saun, &from_len);
    if (msgsock == -1)
            //perror("accept failed");
			return;
    else do {
            memset(buf, 0, len);
            if ((rval  = read(msgsock, buf,  1024)) < 0)
                    perror("reading stream message");
            /*i = 0;
            if (rval == 0)
                    printf("Ending connection\n");
            else
                    printf("-->%s\n", buf);*/
    } while (rval != 0);
    close(msgsock);

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

