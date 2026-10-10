export APP_HKDKFIH_LINKDING_PORT="9095"

# Django CSRF needs every origin the browser may use: the .local name, the hostname and the
# device IPs, over http and https (umbrelOS serves both), plus Tailscale MagicDNS names.
APP_HKDKFIH_LINKDING_HOSTS="${DEVICE_DOMAIN_NAME:-umbrel.local} ${DEVICE_HOSTNAME:-umbrel} $(hostname --all-ip-addresses 2> /dev/null || true)"
APP_HKDKFIH_LINKDING_ORIGINS=""
for APP_HKDKFIH_LINKDING_HOST in ${APP_HKDKFIH_LINKDING_HOSTS}; do
  if [[ "${APP_HKDKFIH_LINKDING_HOST}" == *:* ]]; then
    APP_HKDKFIH_LINKDING_HOST="[${APP_HKDKFIH_LINKDING_HOST}]"
  fi
  APP_HKDKFIH_LINKDING_ORIGINS="${APP_HKDKFIH_LINKDING_ORIGINS}http://${APP_HKDKFIH_LINKDING_HOST}:${APP_HKDKFIH_LINKDING_PORT},https://${APP_HKDKFIH_LINKDING_HOST}:${APP_HKDKFIH_LINKDING_PORT},"
done
export APP_HKDKFIH_LINKDING_TRUSTED_ORIGINS="${APP_HKDKFIH_LINKDING_ORIGINS}http://*.ts.net:${APP_HKDKFIH_LINKDING_PORT},https://*.ts.net:${APP_HKDKFIH_LINKDING_PORT}"
