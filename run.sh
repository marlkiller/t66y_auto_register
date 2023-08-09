#nohup python3 t66y_auto_register.py > app.log &

#!/bin/bash
git pull
# 默认操作为重启
action="restart"

# 检查输入的参数
while [[ $# -gt 0 ]]; do
  case $1 in
    -s|--start)
      action="start"
      ;;
    -t|--stop)
      action="stop"
      ;;
    -r|--restart)
      action="restart"
      ;;
    *)
      echo "Usage: $0 {-s|--start} {-t|--stop} {-r|--restart}"
      exit 1
  esac
  shift
done


print_process_info() {
  p_list=`ps -ef | grep t66y_auto_register.py | grep -v grep`
  echo "$p_list"
}
# 启动
start() {
  echo "Starting process..."
  nohup python3 t66y_auto_register.py > app.log 2>&1 &
  sleep 2
  print_process_info

  tail -f app.log
}

# 停止
stop() {
  echo "Stopping process..."
#  p_list=`ps -ef | grep t66y_auto_register.py | grep -v grep`
  p_list=$(print_process_info)
  echo "$p_list"
  pid_list=`echo "$p_list" | awk '{print $2}'`
  if [[ -n "$pid_list" ]]; then
#    kill -9 $pid_list
#    echo "killed : $pid_list"
    for item  in $pid_list
    do
       kill -s 9 $item
       echo "Stopped : $item"
       sleep 1
    done
  else
    echo "t66y_auto_register.py process is not running"
  fi
}

# 重启
restart() {
  echo "Restarting process..."
  stop
  start
}

case "$action" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    restart
    ;;
esac