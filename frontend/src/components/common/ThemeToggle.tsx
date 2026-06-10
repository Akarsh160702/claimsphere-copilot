import { motion } from 'framer-motion';
import { WeatherMoon20Filled, WeatherSunny20Filled } from '@fluentui/react-icons';
import { useTheme } from '@/contexts/ThemeContext';
import { getPalette } from '@/theme/tokens';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const palette = getPalette(theme);

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      style={{
        position: 'relative',
        width: 64,
        height: 32,
        borderRadius: 999,
        border: `1px solid ${palette.glassBorder}`,
        background: palette.glassFill,
        cursor: 'pointer',
        padding: 0,
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {/* Sliding background */}
      <motion.div
        layout
        initial={false}
        animate={{
          x: theme === 'dark' ? 0 : 32,
        }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 30,
        }}
        style={{
          position: 'absolute',
          width: 28,
          height: 28,
          top: 1,
          left: 1,
          borderRadius: 999,
          background: palette.brand,
          boxShadow: theme === 'dark' 
            ? '0 2px 8px rgba(46, 144, 250, 0.4)'
            : '0 2px 8px rgba(0, 120, 212, 0.3)',
        }}
      />

      {/* Icons */}
      <div
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 6px',
          height: '100%',
          zIndex: 1,
        }}
      >
        <motion.div
          animate={{
            scale: theme === 'dark' ? 1 : 0.7,
            opacity: theme === 'dark' ? 1 : 0.4,
          }}
          transition={{ duration: 0.2 }}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: theme === 'dark' ? '#fff' : palette.textMuted,
          }}
        >
          <WeatherMoon20Filled />
        </motion.div>

        <motion.div
          animate={{
            scale: theme === 'light' ? 1 : 0.7,
            opacity: theme === 'light' ? 1 : 0.4,
          }}
          transition={{ duration: 0.2 }}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: theme === 'light' ? '#fff' : palette.textMuted,
          }}
        >
          <WeatherSunny20Filled />
        </motion.div>
      </div>
    </button>
  );
}
