import sys

def check_master_plan(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_phase_23 = False
    new_lines = []
    
    for line in lines:
        if line.startswith("# PHASE 23"):
            in_phase_23 = True
            
        if not in_phase_23 and line.strip().startswith("- [ ]"):
            line = line.replace("- [ ]", "- [x]")
            
        new_lines.append(line)
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
if __name__ == "__main__":
    check_master_plan("d:\\MumbaiPolice_CyberFraud_Detection\\docs\\mumbai-police-master-plan.md")
