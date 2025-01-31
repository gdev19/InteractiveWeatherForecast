# Weather Forecast Application

This is a simple tool to visualize Weather forecast for the current day. It is built using [Dash](https://dash.plotly.com/), a Python framework for building analytical web applications.

Application is deployed at [codeff.nl](https://www.codeff.nl/apps/weather).

## Features

- Type a location in the search bar to get weather forecast for that location
- Application uses [WeatherApi.com](weatherapi.com) to get weather forecast

## Future work

- Enhance application responsiveness

## Installation

You should register in [WeatherApi.com](weatherapi.com) to get an API key.

Before running the application, you should set the following environment variables:

```
export WEATHER_API_KEY=<your_weather_api_key>
```

For running application locally

```
uv run weather_app.py
```

### Pre-commit

This project uses pre-commit hooks. To install pre-commit, run the following command

```
uv run pre-commit install
```

## Contributing

Feel free to contribute to this project. You can fork the repository and submit a pull request.
