import React from 'react';
import { motion } from 'framer-motion';
import { withStreamlitConnection } from 'streamlit-component-lib';

interface KPIData {
  title: string;
  value: string;
  change: number;
  icon: string;
  color: string;
}

interface KPICardsProps {
  data: KPIData[];
  theme: 'dark' | 'light';
}

const KPICards: React.FC<KPICardsProps> = ({ data, theme }) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const cardVariants = {
    hidden: { 
      opacity: 0, 
      y: 20,
      scale: 0.9
    },
    visible: { 
      opacity: 1, 
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 100,
        damping: 10
      }
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '20px',
        padding: '20px'
      }}
    >
      {data.map((kpi, index) => (
        <motion.div
          key={index}
          variants={cardVariants}
          whileHover={{ 
            scale: 1.05,
            rotateY: 5,
            transition: { duration: 0.2 }
          }}
          style={{
            background: theme === 'dark' 
              ? 'linear-gradient(135deg, #1e3c72, #2a5298)'
              : 'linear-gradient(135deg, #667eea, #764ba2)',
            borderRadius: '20px',
            padding: '25px',
            color: 'white',
            boxShadow: '0 15px 35px rgba(0,0,0,0.3)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.1)',
            cursor: 'pointer'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2 + index * 0.1, type: "spring" }}
                style={{ 
                  fontSize: '2.5rem',
                  marginBottom: '10px'
                }}
              >
                {kpi.icon}
              </motion.div>
              
              <h3 style={{ 
                margin: '0 0 10px 0',
                fontSize: '16px',
                opacity: 0.9,
                fontWeight: 'normal'
              }}>
                {kpi.title}
              </h3>
              
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                style={{
                  fontSize: '2rem',
                  fontWeight: 'bold',
                  marginBottom: '10px'
                }}
              >
                {kpi.value}
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px'
                }}
              >
                <span style={{ 
                  color: kpi.change >= 0 ? '#4caf50' : '#f44336',
                  marginRight: '5px'
                }}>
                  {kpi.change >= 0 ? '↗️' : '↘️'}
                </span>
                <span style={{ opacity: 0.8 }}>
                  {Math.abs(kpi.change).toFixed(1)}% vs período anterior
                </span>
              </motion.div>
            </div>
            
            <motion.div
              animate={{ 
                rotate: [0, 10, -10, 0],
                scale: [1, 1.1, 1]
              }}
              transition={{ 
                duration: 2,
                repeat: Infinity,
                repeatDelay: 3
              }}
              style={{
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${kpi.color}, ${kpi.color}88)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '24px'
              }}
            >
              💎
            </motion.div>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
};

export default withStreamlitConnection(KPICards);
