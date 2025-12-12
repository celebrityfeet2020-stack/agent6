import React from 'react';
import { Cloud, Sun, CloudRain } from 'lucide-react';

interface WeatherCardProps {
  city: string;
  temperature: number;
  condition: string;
  humidity?: number;
}

const WeatherCard: React.FC<WeatherCardProps> = ({ city, temperature, condition, humidity }) => {
  const getWeatherIcon = () => {
    if (condition.includes('雨')) return <CloudRain className="w-12 h-12" />;
    if (condition.includes('云')) return <Cloud className="w-12 h-12" />;
    return <Sun className="w-12 h-12" />;
  };
  
  return (
    <div className="weather-card">
      <div className="weather-icon">{getWeatherIcon()}</div>
      <div className="weather-info">
        <h3 className="text-xl font-bold">{city}</h3>
        <p className="text-3xl">{temperature}°C</p>
        <p className="text-sm text-gray-500">{condition}</p>
        {humidity && <p className="text-xs text-gray-400">湿度: {humidity}%</p>}
      </div>
    </div>
  );
};

export default WeatherCard;
