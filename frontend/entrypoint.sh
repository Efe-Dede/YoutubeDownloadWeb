#!/bin/sh

# Replace the placeholder with the actual API_KEY from environment variables
if [ -n "$API_KEY" ]; then
  echo "Injecting API_KEY into app.js..."
  sed -i "s/\[\[API_KEY_PLACEHOLDER\]\]/$API_KEY/g" /usr/share/nginx/html/js/app.js
else
  echo "Warning: API_KEY not set, using default if available in app.js"
fi

# Execute the original command (Nginx)
exec "$@"
