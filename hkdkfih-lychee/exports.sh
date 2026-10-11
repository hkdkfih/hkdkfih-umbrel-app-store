# Laravel needs a base64 key that decodes to exactly 32 bytes: 43 hex characters plus one "=" of padding.
export APP_HKDKFIH_LYCHEE_APP_KEY="base64:$(derive_entropy "${app_entropy_identifier}-app-key" | cut -c1-43)="
