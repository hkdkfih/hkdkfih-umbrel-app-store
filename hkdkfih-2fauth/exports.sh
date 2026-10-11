# Laravel's AES-256 APP_KEY must be exactly 32 characters; derive_entropy returns 64 hex chars.
APP_HKDKFIH_2FAUTH_KEY_SOURCE="$(derive_entropy "${app_entropy_identifier}-app-key")"
export APP_HKDKFIH_2FAUTH_APP_KEY="${APP_HKDKFIH_2FAUTH_KEY_SOURCE:0:32}"
