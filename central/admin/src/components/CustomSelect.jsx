import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, CheckCircle2 } from 'lucide-react';

const CustomSelect = ({ label, value, options, onChange, placeholder, disabled, icon: Icon = ChevronDown }) => {
  const [isOpen, setIsOpen] = useState(false);
  const selectedOption = options.find(opt => String(opt.id) === String(value));

  return (
    <div className="space-y-1 relative">
      <label className="text-sm font-medium text-muted-foreground ml-1">{label}</label>
      <div className="relative">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
          className={`w-full bg-secondary/30 border border-border rounded-2xl py-3 px-4 flex items-center justify-between transition-all group hover:bg-secondary/50 disabled:opacity-50 disabled:cursor-not-allowed ${isOpen ? 'ring-2 ring-primary/20 border-primary/50 bg-secondary/50' : ''}`}
        >
          <span className={`font-medium ${!selectedOption ? 'text-muted-foreground' : 'text-foreground'}`}>
            {selectedOption ? selectedOption.name : placeholder}
          </span>
          <Icon size={18} className={`text-muted-foreground transition-transform duration-300 ${isOpen ? 'rotate-180 text-primary' : 'group-hover:text-primary'}`} />
        </button>

        <AnimatePresence>
          {isOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute left-0 right-0 mt-2 bg-card border border-border rounded-2xl shadow-2xl z-20 overflow-hidden backdrop-blur-xl"
              >
                <div className="max-h-60 overflow-auto p-2">
                  {options.length > 0 ? (
                    options.map((option) => (
                      <button
                        key={option.id}
                        type="button"
                        onClick={() => {
                          onChange(option.id);
                          setIsOpen(false);
                        }}
                        className={`w-full text-left px-4 py-2.5 rounded-xl transition-all flex items-center justify-between group/opt ${String(value) === String(option.id) ? 'bg-primary text-primary-foreground font-bold shadow-md' : 'hover:bg-secondary text-foreground'}`}
                      >
                        <span className="truncate">{option.name}</span>
                        {String(value) === String(option.id) && <CheckCircle2 size={16} />}
                      </button>
                    ))
                  ) : (
                    <div className="p-4 text-center text-sm text-muted-foreground italic">
                      No options available
                    </div>
                  )}
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default CustomSelect;
