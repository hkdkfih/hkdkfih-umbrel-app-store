# go2rtc runs behind Docker NAT, so WebRTC clients must be told the Umbrel's LAN address.
lan_ip=$(ip -4 route get 1.1.1.1 2> /dev/null | awk '{for (i = 1; i < NF; i++) if ($i == "src") {print $(i + 1); exit}}') || lan_ip=""
export APP_HKDKFIH_GO2RTC_LAN_IP="${lan_ip:-umbrel.local}"
