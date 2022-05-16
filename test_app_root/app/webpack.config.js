const path = require('path');

module.exports = {
    entry: './src/index.js',
    output: {
        filename: '[chunkhash].js',
        path: path.resolve(__dirname, 'public', 'bundle')
    },
    mode: 'production'
};
