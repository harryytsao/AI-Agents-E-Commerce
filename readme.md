# E-commerce Calculator

## Setup Instructions

1. After opening the codespace, install the dependencies:

```bash
pip install -e .
```

2. Configure the required environment variables:

```bash
export OPENAI_API_KEY=<your-openai-api-key>
export DATABASE_URL=<your-database-url>
```

3. Run the application:

```bash
cd ecommerce_calculator
python main.py
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for AI functionality
- `DATABASE_URL`: Connection string for your database (format: `postgresql://user:password@host:port/dbname`)

## Development

For local development, you can create a `.env` file in the root directory with the above environment variables.
