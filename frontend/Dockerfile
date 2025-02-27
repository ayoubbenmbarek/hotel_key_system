FROM node:16-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install

# Copy all files
COPY . .

# Build the application
RUN npm run build

# Expose the port the app will run on
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
