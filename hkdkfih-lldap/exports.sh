export APP_HKDKFIH_LLDAP_JWT_SECRET="$(derive_entropy "${app_entropy_identifier}-jwt-secret")"
export APP_HKDKFIH_LLDAP_KEY_SEED="$(derive_entropy "${app_entropy_identifier}-key-seed")"
