FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# We will run the Vite dev server for the hackathon
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
