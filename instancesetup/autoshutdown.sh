#!/bin/sh
SERVICE='server.jar'
if ps ax | grep -v grep | grep $SERVICE > /dev/null; then
    	PLAYERSEMPTY=" There are 0 of a max 20 players online"
		PLAYERSEMPTY2=" There are 0 of a max of 20 players online"
	$(screen -S minecraft -p 0 -X stuff "list^M")
	sleep 5
	$(screen -S minecraft -p 0 -X stuff "list^M")
	sleep 5
	PLAYERSLIST=$(tail -n 1 /home/ubuntu/logs/latest.log | cut -f2 -d"/" | cut -f2 -d":")
	echo $PLAYERSLIST
	if [ "$PLAYERSLIST" = "$PLAYERSEMPTY" ] || [ "$PLAYERSLIST" = "$PLAYERSEMPTY2" ]
	then
		echo "Waiting for players to come back in 12m, otherwise shutdown"
		sleep 12m
		$(screen -S minecraft -p 0 -X stuff "list^M")
		sleep 5
		$(screen -S minecraft -p 0 -X stuff "list^M")
		sleep 5
		PLAYERSLIST=$(tail -n 1 /home/ubuntu/logs/latest.log | cut -f2 -d"/" | cut -f2 -d":")
		if [ "$PLAYERSLIST" = "$PLAYERSEMPTY" ] || [ "$PLAYERSLIST" = "$PLAYERSEMPTY2" ]
		then
			$(sudo /sbin/shutdown -P +1)
		fi
	fi
else
	echo "Screen does not exist, briefly waiting before trying again"
	sleep 5m
	if ! ps ax | grep -v grep | grep $SERVICE > /dev/null; then
		echo "Screen does not exist, shutting down"
		$(sudo /sbin/shutdown -P +1)
	fi
fi
