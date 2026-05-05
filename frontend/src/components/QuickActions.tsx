import React from "react";
import { motion } from "framer-motion";
import { Calculator, Calendar, User, BookOpen, TrendingUp, CheckSquare } from "lucide-react";

interface QuickActionsProps {
  onAction: (action: string) => void;
  isLoading: boolean;
}

const QuickActions: React.FC<QuickActionsProps> = ({ onAction, isLoading }) => {
  const quickActions = [
    {
      title: "Calculate GPA",
      description: "Custom grades",
      query: "calculate my gpa for my grades c, d, a, b",
      icon: Calculator,
      color: "bg-[#10B981]/20 border-[#10B981]/40 text-[#10B981]"
    },
    {
      title: "Exam Schedule",
      description: "Any course exam",
      query: "when is the exam for MATH201?",
      icon: Calendar,
      color: "bg-[#F59E0B]/20 border-[#F59E0B]/40 text-[#F59E0B]"
    },
    {
      title: "Student Info",
      description: "By student ID",
      query: "who am i? my student id is ST1002",
      icon: User,
      color: "bg-[#6366F1]/20 border-[#6366F1]/40 text-[#6366F1]"
    },
    {
      title: "Register Course",
      description: "Any new course",
      query: "register me for ENG150",
      icon: BookOpen,
      color: "bg-[#8B5CF6]/20 border-[#8B5CF6]/40 text-[#8B5CF6]"
    },
    {
      title: "Grade Prediction",
      description: "With my current grade",
      query: "predict my final grade in PHYS220, my current grade is 65.5",
      icon: TrendingUp,
      color: "bg-[#EC4899]/20 border-[#EC4899]/40 text-[#EC4899]"
    },
    {
      title: "Credit Check",
      description: "Major missing credits",
      query: "how many credits to graduate physics? i have 90",
      icon: CheckSquare,
      color: "bg-[#14B8A6]/20 border-[#14B8A6]/40 text-[#14B8A6]"
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className="rounded-xl border border-[#2A3044] bg-[#161B27] p-6 shadow-lg hover:shadow-[0_0_20px_rgba(99,102,241,0.08)] transition-shadow duration-300"
    >
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 rounded-full bg-[#F59E0B]" />
        <h2
          className="text-sm font-semibold text-[#94A3B8] uppercase tracking-widest"
          style={{ fontFamily: "Space Grotesk, sans-serif" }}
        >
          Quick Actions
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {quickActions.map((action, index) => {
          const Icon = action.icon;
          return (
            <motion.button
              key={index}
              onClick={() => !isLoading && onAction(action.query)}
              disabled={isLoading}
              whileHover={{ scale: isLoading ? 1 : 1.02 }}
              whileTap={{ scale: isLoading ? 1 : 0.98 }}
              className={`flex items-center gap-3 p-3 rounded-lg border transition-all duration-200 ${
                isLoading
                  ? 'opacity-50 cursor-not-allowed'
                  : 'hover:bg-[#0F1117] cursor-pointer'
              } ${action.color}`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <div className="flex-1 text-left">
                <div className="text-xs font-medium" style={{ fontFamily: "Space Grotesk, sans-serif" }}>
                  {action.title}
                </div>
                <div className="text-xs opacity-70" style={{ fontFamily: "Manrope, sans-serif" }}>
                  {action.description}
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
};

export default QuickActions;
