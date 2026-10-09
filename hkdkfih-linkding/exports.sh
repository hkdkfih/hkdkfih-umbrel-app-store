export APP_HKDKFIH_LINKDING_PORT="9095"

# Django CSRF needs every origin the browser may use: device IPs over http and https.
local_ips=$(hostname --all-ip-addresses 2> /dev/null) || local_ips=""
local_origins=""
for ip in $local_ips; do
  if [[ "$ip" == *:* ]]; then
    ip="[$ip]"
  fi
  local_origins="${local_origins}http://${ip}:${APP_HKDKFIH_LINKDING_PORT},https://${ip}:${APP_HKDKFIH_LINKDING_PORT},"
done
export APP_HKDKFIH_LINKDING_LOCAL_ORIGINS="${local_origins%,}"
