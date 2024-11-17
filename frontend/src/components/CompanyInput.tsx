import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Paper } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

interface CompanyInputProps {
  onCompare: (companies: string[]) => void;
  disabled?: boolean;
}

const CompanyInput: React.FC<CompanyInputProps> = ({ onCompare, disabled }) => {
  const [primaryCompany, setPrimaryCompany] = useState('');
  const [competitors, setCompetitors] = useState<string[]>(['']);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const validateCompanyName = (name: string): string | null => {
    if (!name.trim()) {
      return 'Company name is required';
    }
    if (!/^[a-zA-Z0-9\s\-\.]+$/.test(name)) {
      return 'Company name contains invalid characters';
    }
    return null;
  };

  const handleAddCompetitor = () => {
    setCompetitors([...competitors, '']);
    setErrors({});
  };

  const handleRemoveCompetitor = (index: number) => {
    const newCompetitors = competitors.filter((_, i) => i !== index);
    setCompetitors(newCompetitors);
    setErrors({});
  };

  const handleCompetitorChange = (index: number, value: string) => {
    const newCompetitors = [...competitors];
    newCompetitors[index] = value;
    setCompetitors(newCompetitors);
    setErrors({});
  };

  const handleCompare = () => {
    const newErrors: { [key: string]: string } = {};
    
    // Validate primary company
    const primaryError = validateCompanyName(primaryCompany);
    if (primaryError) {
      newErrors.primary = primaryError;
    }

    // Validate competitors
    competitors.forEach((comp, index) => {
      if (comp.trim()) {
        const error = validateCompanyName(comp);
        if (error) {
          newErrors[`competitor${index}`] = error;
        }
      }
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    const validCompanies = [
      primaryCompany,
      ...competitors.filter(c => c.trim() !== '')
    ];
    onCompare(validCompanies);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Compare Products
      </Typography>
      
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Primary Company"
          value={primaryCompany}
          onChange={(e) => setPrimaryCompany(e.target.value)}
          variant="outlined"
          disabled={disabled}
          error={!!errors.primary}
          helperText={errors.primary}
        />
      </Box>

      {competitors.map((competitor, index) => (
        <Box key={index} sx={{ mb: 2, display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            label={`Competitor ${index + 1}`}
            value={competitor}
            onChange={(e) => handleCompetitorChange(index, e.target.value)}
            variant="outlined"
            disabled={disabled}
            error={!!errors[`competitor${index}`]}
            helperText={errors[`competitor${index}`]}
          />
          {competitors.length > 1 && (
            <Button
              variant="outlined"
              color="error"
              onClick={() => handleRemoveCompetitor(index)}
              disabled={disabled}
            >
              <DeleteIcon />
            </Button>
          )}
        </Box>
      ))}

      <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
        <Button
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={handleAddCompetitor}
          disabled={disabled || competitors.length >= 5}
        >
          Add Competitor
        </Button>
        <Button
          variant="contained"
          onClick={handleCompare}
          disabled={disabled || !primaryCompany || competitors.every(c => !c.trim())}
        >
          Compare Products
        </Button>
      </Box>
    </Paper>
  );
};

export default CompanyInput;
