var config = require('./webpack.base.config.js');

config.mode = 'production'; // causes libs like React to exclude debugging code
config.optimization.minimize = true;
config.devtool = false;
module.exports = config;

