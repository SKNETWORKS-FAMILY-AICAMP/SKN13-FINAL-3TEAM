#!/bin/sh
# wait-for-it.sh

set -e

host="$1"
shift
cmd="$@"

# host가 사용 가능해질 때까지 1초마다 루프를 돌며 대기합니다.
# nc (netcat)을 사용하여 특정 host의 포트가 열렸는지 확인합니다.
until nc -z "$host"; do
  >&2 echo "Host $host is unavailable - sleeping"
  sleep 1
done

>&2 echo "Host $host is up - executing command"
exec $cmd   