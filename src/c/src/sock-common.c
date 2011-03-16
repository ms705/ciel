
#include "sock-common.h"

uint8_t my_id;
char my_addr[18];

void sock_set_id(uint8_t id) {

	my_id = id;
	sprintf(my_addr, "192.168.0.%d", my_id+1);

	printf("set my address to %s\n", my_addr);

}


int sock_init_server(int *sock, uint8_t blocking) {

	register int len;
	struct sockaddr_in saun;


	// Get a streaming UNIX domain socket
	if ((*sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		perror("socket creation error");
		return 1;
	}

	// Create the address to connect to
	saun.sin_family = AF_INET;
	//strcpy(saun.sin_addr, my_addr);
	saun.sin_port = htons(9001);
	//inet_pton(AF_INET, my_addr)
	saun.sin_addr.s_addr = htonl(INADDR_ANY);

	// delete the socket file if it still exists
	unlink(my_addr);

	//len = sizeof(saun.sin_family) + strlen(saun.sin_addr);

	if (bind(*sock, (const struct sockaddr *)&saun, sizeof(saun)) < 0) {
		perror("failed to bind to socket");
		return 1;
	}

	if (listen(*sock, 5) < 0) {
		perror("failed to listen on socket");
		return 1;
	}

	// Make the socket non-blocking
	if (!blocking) sock_set_nonblock(*sock);

	return 0;
}


int sock_init_client(int *sockid) {

	// Get a streaming UNIX domain socket
	if ((*sockid = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		perror("socket creation error");
		return -1;
	}

	return 0;

}


void sock_send(int remote_id, char *data, size_t len) {

	struct sockaddr_in saun;
	register int slen;
	int s;

	sock_init_client(&s);

	// Create the address to connect to
	saun.sin_family = AF_INET;
	char *remote_addr = get_remote_addr(remote_id);
	//strcpy(saun.sin_path, remote_addr);
	saun.sin_addr.s_addr = inet_addr(remote_addr);
	saun.sin_port = htons(9001);

	//slen = sizeof(saun.sin_family) + strlen(saun.sin_path);

	printf("sending to socket at address %s, port %d\n", remote_addr, ntohs(saun.sin_port));

	if (connect(s, (const struct sockaddr *)&saun, sizeof(saun)) < 0) {
		perror("failed to connect to socket");
		exit(1);
	}

	send(s, data, len, 0);

	close(s);

	free(remote_addr);

}

int32_t sock_recv(int sockfd, char *buf, unsigned int len) {

	struct sockaddr_in from_saun;
	socklen_t from_len;
	int32_t rval;
	int32_t n_read = 0;

	int msgsock = accept(sockfd, (const struct sockaddr *)&from_saun, &from_len);
	//printf("accepted from %s\n", from_saun.sun_path);
	if (msgsock == -1) {
		perror("accept failed, or non-blocking mode");
		return -1;
	} else {
		memset(buf, 0, len);
		while (n_read < len) {
			if ((rval = read(msgsock, buf,  len)) < 0)
				perror("failed to read from socket");
			//printf("read %d bytes, expected %d, continuing\n", n_read, len);
			n_read += rval;
		}
		/*if (rval == 0)
				printf("Ending connection\n");
		else
				printf("-->%s\n", buf);*/
	}
	close(msgsock);

	//printf("read %d bytes, expected %d\n", n_read, len);

	return n_read;
}


void sock_set_nonblock(int socket) {
	int flags;
	flags = fcntl(socket,F_GETFL,0);
	assert(flags != -1);
	fcntl(socket, F_SETFL, flags | O_NONBLOCK);
}

#if 0
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
#endif


static char * get_remote_addr(uint8_t id) {

	char *remote_addr = (char *)malloc(18*sizeof(char));
	sprintf(remote_addr, "192.168.0.%d", id+1);

	return remote_addr;

}
