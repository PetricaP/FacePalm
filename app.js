const express = require('express');
const expressLayouts = require('express-ejs-layouts');
const bodyParser = require('body-parser');

const app = express();

const port = 9090

app.set('view engine', 'ejs');

app.use(expressLayouts);

app.use(express.static('static'));

app.use(bodyParser.json());

app.use(bodyParser.urlencoded({ extended: true }));

app.get('/', (req, res) => {
    res.render('UI/index.html');
});

app.listen(port, '0.0.0.0', () => console.log(`Server running on http://0.0.0.0${port}`));
