module.exports = {
  devServer: {
    // This overrides the webpack-dev-server configuration
    setupMiddlewares: (middlewares, devServer) => {
      // Add any custom middleware here if needed
      return middlewares;
    }
  }
}; 