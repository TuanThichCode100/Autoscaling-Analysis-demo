import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export const ThemeToggle: React.FC = () => {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className={`
        p-2 rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
        ${theme === 'light'
                    ? 'bg-slate-100 text-amber-500 hover:bg-slate-200 focus:ring-amber-400'
                    : 'bg-slate-800 text-blue-400 hover:bg-slate-700 focus:ring-blue-500'}
      `}
            aria-label="Toggle Theme"
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
        >
            {theme === 'light' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
    );
};
