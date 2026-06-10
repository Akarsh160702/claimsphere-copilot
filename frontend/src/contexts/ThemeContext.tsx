import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Theme } from '@/theme/tokens';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Check localStorage or default to dark
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('claimsphere-theme');
    return (saved === 'light' || saved === 'dark') ? saved : 'dark';
  });

  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('claimsphere-theme', theme);
    
    // Update document data attribute for CSS
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update color-scheme for native elements
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
