var path = require("path");
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  mode: "development",
  context: __dirname,

  plugins: [
    new webpack.ProvidePlugin({
        $: "jquery",
        jQuery: "jquery"
    }),
    new BundleTracker({filename: './webpack-stats.json'}),
    new webpack.optimize.OccurrenceOrderPlugin()
  ],

  performance: {
    maxEntrypointSize: 750000,
    maxAssetSize: 750000
  },

  entry: {
    project: './bakround_applicant/static/js/project.js',
    employer_search: './bakround_applicant/static/js/employer_search.jsx',
    icims_search: './bakround_applicant/static/js/icims_search.jsx',
    employer_job: './bakround_applicant/static/js/employer_job.jsx',
    icims_job: './bakround_applicant/static/js/icims_job.jsx',
    manual_verifier: './bakround_applicant/static/js/manual_verifier.jsx'
  },

  output: {
      path: path.resolve('./bakround_applicant/static/bundles/'),
      filename: "[name].js"
  },

  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: [{loader: 'babel-loader'}]
      },
      {
        test: /\.css$/,
        use: [{loader: 'style-loader'}, {loader: 'css-loader'}]
      }
    ]
  },
  watchOptions: {
    ignored: /node_modules/
  },
  devtool: 'source-map',
  resolve: {
    modules: ['node_modules', 'bower_components'],
    extensions: ['.js', '.jsx']
  },
  optimization: {
    noEmitOnErrors: true
  }
};
