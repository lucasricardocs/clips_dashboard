import React, { useEffect, useRef, useState } from 'react';
import { Streamlit, withStreamlitConnection } from 'streamlit-component-lib';
import * as d3 from 'd3';
import { motion, AnimatePresence } from 'framer-motion';

interface ChartData {
  date: string;
  cartao: number;
  dinheiro: number;
  pix: number;
  total: number;
}

interface AnimatedChartProps {
  data: ChartData[];
  chartType: 'line' | 'bar' | 'area';
  theme: 'dark' | 'light';
}

const AnimatedChart: React.FC<AnimatedChartProps> = ({ data, chartType, theme }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [animationStep, setAnimationStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!data || data.length === 0) return;
    
    const svg = d3.select(svgRef.current);
    const width = 800;
    const height = 400;
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };

    // Limpar SVG anterior
    svg.selectAll("*").remove();

    // Configurar escalas
    const xScale = d3.scaleTime()
      .domain(d3.extent(data, d => new Date(d.date)) as [Date, Date])
      .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.total) || 0])
      .range([height - margin.bottom, margin.top]);

    // Cores baseadas no tema
    const colors = theme === 'dark' 
      ? { primary: '#64ffda', secondary: '#ff6b35', tertiary: '#4caf50', background: '#1a1a2e' }
      : { primary: '#1976d2', secondary: '#f57c00', tertiary: '#388e3c', background: '#ffffff' };

    // Criar gradientes animados
    const defs = svg.append("defs");
    
    const gradient = defs.append("linearGradient")
      .attr("id", "areaGradient")
      .attr("gradientUnits", "userSpaceOnUse")
      .attr("x1", 0).attr("y1", height)
      .attr("x2", 0).attr("y2", 0);

    gradient.append("stop")
      .attr("offset", "0%")
      .attr("stop-color", colors.primary)
      .attr("stop-opacity", 0);

    gradient.append("stop")
      .attr("offset", "100%")
      .attr("stop-color", colors.primary)
      .attr("stop-opacity", 0.8);

    // Função de linha
    const line = d3.line<ChartData>()
      .x(d => xScale(new Date(d.date)))
      .y(d => yScale(d.total))
      .curve(d3.curveCardinal);

    // Função de área
    const area = d3.area<ChartData>()
      .x(d => xScale(new Date(d.date)))
      .y0(height - margin.bottom)
      .y1(d => yScale(d.total))
      .curve(d3.curveCardinal);

    // Adicionar eixos com animação
    svg.append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat("%d/%m")))
      .selectAll("text")
      .style("fill", theme === 'dark' ? '#ffffff' : '#000000')
      .style("opacity", 0)
      .transition()
      .duration(1000)
      .style("opacity", 1);

    svg.append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(yScale))
      .selectAll("text")
      .style("fill", theme === 'dark' ? '#ffffff' : '#000000')
      .style("opacity", 0)
      .transition()
      .duration(1000)
      .style("opacity", 1);

    if (chartType === 'area') {
      // Área animada
      const path = svg.append("path")
        .datum(data)
        .attr("fill", "url(#areaGradient)")
        .attr("d", area);

      const totalLength = path.node()?.getTotalLength() || 0;
      
      path
        .attr("stroke-dasharray", totalLength + " " + totalLength)
        .attr("stroke-dashoffset", totalLength)
        .transition()
        .duration(2000)
        .ease(d3.easeLinear)
        .attr("stroke-dashoffset", 0);
    }

    if (chartType === 'line' || chartType === 'area') {
      // Linha principal animada
      const path = svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", colors.primary)
        .attr("stroke-width", 3)
        .attr("d", line);

      const totalLength = path.node()?.getTotalLength() || 0;
      
      path
        .attr("stroke-dasharray", totalLength + " " + totalLength)
        .attr("stroke-dashoffset", totalLength)
        .transition()
        .duration(2000)
        .ease(d3.easeLinear)
        .attr("stroke-dashoffset", 0);

      // Pontos animados
      svg.selectAll(".dot")
        .data(data)
        .enter().append("circle")
        .attr("class", "dot")
        .attr("cx", d => xScale(new Date(d.date)))
        .attr("cy", d => yScale(d.total))
        .attr("r", 0)
        .attr("fill", colors.secondary)
        .transition()
        .delay((d, i) => i * 100)
        .duration(500)
        .attr("r", 5)
        .on("end", function() {
          d3.select(this)
            .on("mouseover", function(event, d) {
              // Tooltip animado
              const tooltip = svg.append("g")
                .attr("class", "tooltip")
                .attr("transform", `translate(${xScale(new Date(d.date))}, ${yScale(d.total) - 10})`);

              tooltip.append("rect")
                .attr("x", -40)
                .attr("y", -25)
                .attr("width", 80)
                .attr("height", 20)
                .attr("fill", colors.background)
                .attr("stroke", colors.primary)
                .attr("rx", 5)
                .style("opacity", 0)
                .transition()
                .duration(200)
                .style("opacity", 0.9);

              tooltip.append("text")
                .attr("text-anchor", "middle")
                .attr("y", -10)
                .style("fill", theme === 'dark' ? '#ffffff' : '#000000')
                .style("font-size", "12px")
                .text(`R$ ${d.total.toLocaleString('pt-BR')}`)
                .style("opacity", 0)
                .transition()
                .duration(200)
                .style("opacity", 1);
            })
            .on("mouseout", function() {
              svg.select(".tooltip").remove();
            });
        });
    }

    if (chartType === 'bar') {
      // Barras animadas
      svg.selectAll(".bar")
        .data(data)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", d => xScale(new Date(d.date)) - 10)
        .attr("y", height - margin.bottom)
        .attr("width", 20)
        .attr("height", 0)
        .attr("fill", colors.primary)
        .transition()
        .delay((d, i) => i * 50)
        .duration(800)
        .attr("y", d => yScale(d.total))
        .attr("height", d => height - margin.bottom - yScale(d.total));
    }

    // Configurar altura do frame
    Streamlit.setFrameHeight(height + 50);

  }, [data, chartType, theme, animationStep]);

  // Controles de animação
  const playAnimation = () => {
    setIsPlaying(true);
    const interval = setInterval(() => {
      setAnimationStep(prev => {
        if (prev >= data.length - 1) {
          setIsPlaying(false);
          clearInterval(interval);
          return 0;
        }
        return prev + 1;
      });
    }, 500);
  };

  return (
    <div style={{ 
      background: theme === 'dark' ? '#1a1a2e' : '#ffffff',
      borderRadius: '15px',
      padding: '20px',
      boxShadow: '0 15px 35px rgba(0,0,0,0.2)'
    }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '20px'
        }}>
          <h3 style={{ 
            color: theme === 'dark' ? '#64ffda' : '#1976d2',
            margin: 0,
            fontSize: '24px'
          }}>
            📊 Vendas Interativas
          </h3>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={playAnimation}
            disabled={isPlaying}
            style={{
              background: 'linear-gradient(135deg, #ff6b35, #f7931e)',
              color: 'white',
              border: 'none',
              borderRadius: '25px',
              padding: '10px 20px',
              cursor: isPlaying ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 'bold'
            }}
          >
            {isPlaying ? '⏸️ Pausar' : '▶️ Animar'}
          </motion.button>
        </div>

        <svg
          ref={svgRef}
          width="800"
          height="400"
          style={{ background: 'transparent' }}
        />
      </motion.div>
    </div>
  );
};

export default withStreamlitConnection(AnimatedChart);
