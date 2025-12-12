import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface DataChartProps {
  data: Array<Record<string, any>>;
  xKey: string;
  yKey: string;
  title?: string;
}

/**
 * 数据图表 (Generative UI示例)
 * 
 * Agent可以在数据分析后动态生成图表
 */
const DataChart: React.FC<DataChartProps> = ({ data, xKey, yKey, title }) => {
  return (
    <div className="data-chart-card">
      {title && <h3 className="data-chart-title">{title}</h3>}
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey={yKey} fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default DataChart;
