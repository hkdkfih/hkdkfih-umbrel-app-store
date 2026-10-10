# go2rtc runs behind Docker NAT, so WebRTC clients must be told the Umbrel's LAN address.
APP_HKDKFIH_GO2RTC_ROUTE_IP=$(ip -4 route get 1.1.1.1 2> /dev/null | awk '{for (i = 1; i < NF; i++) if ($i == "src") {print $(i + 1); exit}}') || APP_HKDKFIH_GO2RTC_ROUTE_IP=""
export APP_HKDKFIH_GO2RTC_LAN_IP="${APP_HKDKFIH_GO2RTC_ROUTE_IP:-umbrel.local}"
