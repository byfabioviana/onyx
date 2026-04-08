FROM nginx:1.25.5-alpine

RUN apk add --no-cache curl

# Copy nginx templates into the image
COPY templates/ /nginx-templates/

# Default command (overridden by stack)
CMD ["nginx", "-g", "daemon off;"]
