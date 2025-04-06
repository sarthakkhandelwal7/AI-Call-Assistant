FROM node:16-alpine

# Declare build arguments
ARG REACT_APP_GOOGLE_CLIENT_ID

# Set environment variables from build arguments for the build process
ENV REACT_APP_GOOGLE_CLIENT_ID=$REACT_APP_GOOGLE_CLIENT_ID

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
