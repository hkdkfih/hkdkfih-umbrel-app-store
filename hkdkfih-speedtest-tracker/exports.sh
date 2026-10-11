export APP_HKDKFIH_SPEEDTEST_TRACKER_APP_KEY="base64:$(printf '%s' "$(derive_entropy "${app_entropy_identifier}-app-key" | head -c32)" | base64)"
