# Deployment Guide for ICU Occupancy Predictor

This guide will help you deploy your ARIMA model for pediatric ICU bed occupancy prediction on Render.

## Prerequisites

1. A Render account (free tier available)
2. Your trained ARIMA model saved as `models/arima_model1.pkl`
3. Git repository with your code

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your repository contains:

- `run.py` - Flask application entry point
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `gunicorn.conf.py` - Gunicorn configuration
- `app/` - Flask application code
- `models/arima_model1.pkl` - Your trained ARIMA model

### 2. Deploy on Render

1. **Sign up/Login to Render**

   - Go to [render.com](https://render.com)
   - Create an account or sign in

2. **Connect Your Repository**

   - Click "New +" and select "Web Service"
   - Connect your GitHub/GitLab repository
   - Select the repository containing your code

3. **Configure the Service**

   - **Name**: `icu-occupancy-predictor` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app --bind 0.0.0.0:$PORT`

4. **Environment Variables** (Optional)

   - `SECRET_KEY`: A secure secret key for Flask
   - `FLASK_ENV`: `production`

5. **Database Setup**

   - Render will automatically create a PostgreSQL database
   - The `DATABASE_URL` environment variable will be automatically set

6. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application

### 3. Verify Deployment

Once deployed, you can test your API endpoints:

1. **Health Check**

   ```
   GET https://your-app-name.onrender.com/api/health
   ```

2. **Model Information**

   ```
   GET https://your-app-name.onrender.com/api/predict/occupancy
   ```

3. **Make Predictions**

   ```
   POST https://your-app-name.onrender.com/api/predict/occupancy
   Content-Type: application/json

   {
     "weeks_ahead": 1
   }
   ```

## API Endpoints

### Health Check

- **URL**: `/api/health`
- **Method**: `GET`
- **Description**: Check if the service and model are running

### Model Info

- **URL**: `/api/predict/occupancy`
- **Method**: `GET`
- **Description**: Get information about the prediction model

### Predict Occupancy

- **URL**: `/api/predict/occupancy`
- **Method**: `POST`
- **Body**: `{"weeks_ahead": 1}` (optional, defaults to 1)
- **Description**: Predict ICU occupancy for the specified number of weeks

## Troubleshooting

### Common Issues

1. **Model Loading Error**

   - Ensure `models/arima_model1.pkl` is in your repository
   - Check file permissions

2. **Database Connection Error**

   - Verify `DATABASE_URL` environment variable is set
   - Check database credentials

3. **Build Failures**

   - Review build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`

4. **Memory Issues**
   - The free tier has memory limits
   - Consider upgrading for production use

### Logs

- View logs in the Render dashboard
- Check application logs for errors
- Monitor database connection issues

## Local Testing

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python run.py

# Test endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/predict/occupancy
```

## Security Considerations

1. **Environment Variables**: Never commit sensitive data
2. **API Keys**: Use environment variables for any API keys
3. **Database**: Use strong passwords for production databases
4. **HTTPS**: Render provides HTTPS by default

## Scaling

- **Free Tier**: Limited resources, suitable for testing
- **Paid Plans**: Better performance and reliability
- **Custom Domains**: Available on paid plans

## Support

- Render Documentation: [docs.render.com](https://docs.render.com)
- Flask Documentation: [flask.palletsprojects.com](https://flask.palletsprojects.com)
- StatsModels Documentation: [statsmodels.org](https://statsmodels.org)
