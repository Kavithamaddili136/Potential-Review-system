import streamlit as st
import pandas as pd
import base64,random
import time,datetime
import matplotlib.colors as mcolors
import gensim
import gensim.corpora as corpora
from operator import index
from wordcloud import WordCloud
from pandas._config.config import options
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import Similar

from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io,random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos,Backend_course
import pafy
import plotly.express as px


# Reading the CSV files prepared by the fileReader.py
Resumes = pd.read_csv('Resume_Data.csv')
Jobs = pd.read_csv('Job_Data.csv')



def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title

def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

connection = pymysql.connect(host='localhost',user='root',password='',db='sra1')
cursor = connection.cursor()

def insert_data(name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, str(res_score), timestamp,str(no_of_pages), reco_field, cand_level, skills,recommended_skills,courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

st.set_page_config(
   page_title="Potential Review System",
   page_icon='./Logo/logo.ico',
)
def run():
    st.title("Potential Review System")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    # link = '[©Developed by Spidy20](http://github.com/spidy20)'
    # st.sidebar.markdown(link, unsafe_allow_html=True)
    img = Image.open('./Logo/logo.jpg')
    img = img.resize((600,250))
    st.image(img)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    if choice == 'Normal User':
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello "+ resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown( '''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >=3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)

                st.subheader("**Skills Recommendation💡**")
                ## Skill shows
                keywords = st_tags(label='### Skills that you have',
                text='See our skills recommendation',
                    value=resume_data['skills'],key = '1')

                ##  recommendation
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                Backend_keyword = ['python','java','PHP','SQL','git','HTML','CSS','JavaScript','nodeJS','ExpressJS','Django',' PostgreSQL','MongoDB','DSA']
                frontend_keyword = ['HTML','CSS','JavaScript','Jquery','Typescript','AJAX','JSON','Bootstrap','angular','reactJs','NodeJs']
                fullstack_keyword = ['HTML','CSS','JavaScript','Jquery','Typescript','AJAX','JSON','Bootstrap','angular','reactJs','NodeJs','python','java','PHP','SQL','git','HTML','CSS','JavaScript','nodeJS','ExpressJS','Django',' PostgreSQL','MongoDB','DSA']
                testing_keyword =  ['HTML','CSS','JavaScript','Jquery','Typescript','SOAP','API','REST','SQL','Testsigma','Selenium','UFT/QTP','Nessus','Selendroid','SoapUI' ]
                analyst_keyword = ['R','python','SQL','Machine Learning','MATLAB']
                network_keyword = ['Ruby','perl','python','IOT','DNS','MPLS']
                
                recommended_skills = []
                reco_field = ''
                rec_course = ''
                ## Courses recommendation
                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                    ## Backend Developer recommendation
                    elif i.lower() in Backend_keyword:
                        print(i.lower())
                        reco_field = 'Backend Developer'
                        st.success("** Our analysis says you are looking for Backend Developer Jobs **")
                        recommended_skills = ['python','java','PHP','SQL','git','HTML','CSS','JavaScript','nodeJS','ExpressJS','Django',' PostgreSQL','MongoDB','DSA']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '7')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(Backend_course)
                        break

                    ## Frontend Developer recommendation
                    elif i.lower() in frontend_keyword:
                        print(i.lower())
                        reco_field = 'frontend_keyword'
                        st.success("** Our analysis says you are looking for frontend Developer Jobs **")
                        recommended_skills = ['HTML','CSS','JavaScript','Jquery','Typescript','AJAX','JSON','Bootstrap','angular','reactJs','NodeJs']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '8')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(frontend_course)
                        break

                    ## Full Stack Developer Recommendation
                    elif i.lower() in fullstack_keyword:
                        print(i.lower())
                        reco_field = 'Full Stack Developer'
                        st.success("** Our analysis says you are looking for Full Stcck Developer Jobs **")
                        recommended_skills = ['HTML','CSS','JavaScript','Jquery','Typescript','AJAX','JSON','Bootstrap','angular','reactJs','NodeJs','python','java','PHP','SQL','git','HTML','CSS','JavaScript','nodeJS','ExpressJS','Django',' PostgreSQL','MongoDB','DSA']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '9')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(fullstack_course)
                        break

                    ## software tester Recommendation
                    elif i.lower() in testing_keyword:
                        print(i.lower())
                        reco_field = 'software tester'
                        st.success("** Our analysis says you are looking for software tester Jobs **")
                        recommended_skills = ['HTML','CSS','JavaScript','Jquery','Typescript','SOAP','API','REST','SQL','Testsigma','Selenium','UFT/QTP','Nessus','Selendroid','SoapUI' ]
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '10')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(testing_course)
                        break


                    ## Data Analyst Recommendation
                    elif i.lower() in analyst_keyword:
                        print(i.lower())
                        reco_field = 'Data Analyst'
                        st.success("** Our analysis says you are looking for Data Analyst Jobs **")
                        recommended_skills = ['R','python','SQL','Machine Learning','MATLAB']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '11')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(analyst_course)
                        break

                    ## Network Engineer recommendation
                    elif i.lower() in network_keyword:
                        print(i.lower())
                        reco_field = 'Network Engineer'
                        st.success("** Our analysis says you are looking for Network Engineer Jobs **")
                        recommended_skills = ['Ruby','perl','python','IOT','DNS','MPLS']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '12')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(network_course)
                        break

                
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)

                 ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score+20
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'Declaration'  in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration✍/h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',unsafe_allow_html=True)

                if 'Hobbies' or 'Interests'in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)

                if 'Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)

               
            
            
            else:
                st.error('Something went wrong..')
            ## calculating user resume score
            resume_score = len(recommended_skills) / len(recommended_skills) * 100

            print("Resume Score: {}%".format(resume_score))
              
            
    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'resumescreening' and ad_password == 'resume123':
                st.success("Welcome Team 51")
###############################################################################
        # Checking for Multiple Job Descriptions
# If more than one Job Descriptions are available, it asks user to select one as well.
                if len(Jobs['Name']) <= 1:
                    st.write("There is only 1 Job Description present. It will be used to create scores.")
                else:
                    st.write("There are ", len(Jobs['Name']),"Job Descriptions available. Please select one.")

# Asking to Print the Job Desciption Names
                if len(Jobs['Name']) > 1:
                    option_yn = st.selectbox("Should we need to Show the Job Description Names?", options=['YES', 'NO'])
                    if option_yn == 'YES':
                        index = [a for a in range(len(Jobs['Name']))]
                        fig = go.Figure(data=[go.Table(header=dict(values=["Job No.", "Job Desc. Name"], line_color='black',fill_color='lightskyblue'),cells=dict(values=[index, Jobs['Name']], line_color='black',fill_color='white'))])
                        fig.update_layout(width=700, height=400)
                        st.write(fig)
###########################################################################################################  
# Asking to chose the Job Description
                index = st.slider("Slide to select te JD : ", 0,
                                  len(Jobs['Name'])-1, 1)
                option_yn = st.selectbox("Do you want Job Description to be displayed ?", options=['YES', 'NO'])
                if option_yn == 'YES':
                    st.markdown("---")
                    st.markdown("### Job Description :")
                    fig = go.Figure(data=[go.Table(header=dict(values=["Job Description"],
                                    fill_color='#f0a500',align='center', font=dict(color='black', size=16)),
                                    cells=dict(values=[Jobs['Context'][index]],
                                               fill_color='#f4f4f4',align='left'))])
                    fig.update_layout(width=800, height=500)
                    m = Jobs['Context'][index]
                    st.write(m)
                    st.markdown("---")


#################################### SCORE CALCUATION ################################
                @st.cache()
                def calculate_scores(resumes, job_description):
                    scores = []
                    for x in range(resumes.shape[0]):
                        score = Similar.match(resumes['TF_Based'][x], job_description['TF_Based'][index])
                        scores.append(score)
                    return scores
                Resumes['Scores'] = calculate_scores(Resumes, Jobs)
                Ranked_resumes = Resumes.sort_values(by=['Scores'], ascending=False).reset_index(drop=True)
                Ranked_resumes['Rank'] = pd.DataFrame(
                    [i for i in range(1, len(Ranked_resumes['Scores'])+1)])

###################################### SCORE TABLE PLOT ####################################
                fig1 = go.Figure(data=[go.Table(header=dict(values=["Rank", "Name", "Scores"],fill_color='#00416d',align='center', 
                                                            font=dict(color='black', size=16)),cells=dict(values=[Ranked_resumes.Rank, Ranked_resumes.Name, Ranked_resumes.Scores],
                                                                                                          fill_color='#000000',align='left'))])
                fig1.update_layout(title="Top Ranked Resumes", width=700, height=1100)
                cont = """{},{},{}""".format(Ranked_resumes.Rank, Ranked_resumes.Name, Ranked_resumes.Scores)
# st.write(cont)
                st.write(Ranked_resumes.Rank, Ranked_resumes.Name, Ranked_resumes.Scores)
                st.markdown("---")
                fig2 = px.bar(Ranked_resumes,x=Ranked_resumes['Name'], y=Ranked_resumes['Scores'], color='Scores',color_continuous_scale='haline', title="Score and Rank Distribution")
# fig.update_layout(width=700, height=700)
                st.write(fig2)
                st.markdown("---")

############################################ TF-IDF Code ###################################
                @st.cache()
                def get_list_of_words(document):
                    Document = []
                    for a in document:
                        raw = a.split(" ")
                        Document.append(raw)
                    return Document
                document = get_list_of_words(Resumes['Cleaned'])
                id2word = corpora.Dictionary(document)
                corpus = [id2word.doc2bow(text) for text in document]
                lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus, id2word=id2word, num_topics=6, random_state=100,
                                            update_every=3, chunksize=100, passes=50, alpha='auto', per_word_topics=True)

################################### LDA CODE ##############################################
                @st.cache  # Trying to improve performance by reducing the rerun computations
                def format_topics_sentences(ldamodel, corpus):
                    sent_topics_df = []
                    for i, row_list in enumerate(ldamodel[corpus]):
                        row = row_list[0] if ldamodel.per_word_topics else row_list
                        row = sorted(row, key=lambda x: (x[1]), reverse=True)
                        for j, (topic_num, prop_topic) in enumerate(row):
                            if j == 0:
                                wp = ldamodel.show_topic(topic_num)
                                topic_keywords = ", ".join([word for word, prop in wp])
                                sent_topics_df.append([i, int(topic_num), round(prop_topic, 4)*100, topic_keywords])
                            else:
                                break
                    return sent_topics_df


################################# Topic Word Cloud Code #####################################
                st.markdown("## Topics and Topic Related Keywords ")
                st.markdown( """This Wordcloud representation shows the Topic Number and the Top Keywords that contstitute a Topic.
                              This further is used to cluster the resumes.      """)
                cols = [color for name, color in mcolors.TABLEAU_COLORS.items()]
                cloud = WordCloud(background_color='white',width=2500,height=1800,max_words=10,colormap='tab10',collocations=False,color_func=lambda *args, **kwargs: cols[i],prefer_horizontal=1.0)
                topics = lda_model.show_topics(formatted=False)
                fig, axes = plt.subplots(2, 3, figsize=(10, 10), sharex=True, sharey=True)
                for i, ax in enumerate(axes.flatten()):
                    fig.add_subplot(ax)
                    topic_words = dict(topics[i][1])
                    cloud.generate_from_frequencies(topic_words, max_font_size=300)
                    plt.gca().imshow(cloud)
                    plt.gca().set_title('Topic ' + str(i), fontdict=dict(size=16))
                    plt.gca().axis('off')
                plt.subplots_adjust(wspace=0, hspace=0)
                plt.axis('off')
                plt.margins(x=0, y=0)
                plt.tight_layout()
                st.pyplot(plt)
                st.markdown("---")

####################### SETTING UP THE DATAFRAME FOR SUNBURST-GRAPH ############################
                df_topic_sents_keywords = format_topics_sentences(ldamodel=lda_model, corpus=corpus)
                df_some = pd.DataFrame(df_topic_sents_keywords, columns=['Document No', 'Dominant Topic', 'Topic % Contribution', 'Keywords'])
                df_some['Names'] = Resumes['Name']
                df = df_some
                st.markdown("## Topic Modeling with Resume using LDA ")
                st.markdown("Using LDA to divide the topics into a number of usefull topics and creating a Cluster of matching topic resumes.  ")
                fig3 = px.sunburst(df, path=['Dominant Topic', 'Names'], values='Topic % Contribution',
                   color='Dominant Topic', color_continuous_scale='viridis', width=800, height=800, title="Topic Distribution Graph")
                st.write(fig3)


############################## RESUME PRINTING #############################
                option_2 = st.selectbox("Do you want to see the Best Resumes?", options=['YES', 'NO'])
                if option_2 == 'YES':
                    indx = st.slider("Slide, Which resume to display ?:", 1, Ranked_resumes.shape[0], 1)
                    st.write("Displaying Resume with Rank: ", indx)
                    st.markdown("---")
                    st.markdown("## **Resume** ")
                    value = Ranked_resumes.iloc[indx-1, 2]
                    st.markdown("#### The Word Cloud For Resume")
                    wordcloud = WordCloud(width=800, height=800,background_color='black',colormap='viridis', collocations=False,min_font_size=10).generate(value)
                    plt.figure(figsize=(7, 7), facecolor=None)
                    plt.imshow(wordcloud)
                    plt.axis("off")
                    plt.tight_layout(pad=0)
                    st.pyplot(plt)
                    st.write("With a Match Score of :", Ranked_resumes.iloc[indx-1, 6])
                    fig = go.Figure(data=[go.Table(header=dict(values=["Resume"],fill_color='#000000',align='center', font=dict(color='black', size=16)),cells=dict(values=[str(value)],
                   fill_color='#f4f4f4',
                   align='left'))])
                    fig.update_layout(width=800, height=1200)
    # st.write(fig)
                    st.write(str(value))
                    st.markdown("---")
##############################################################################################    
            # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

    


            else:
                st.error("Wrong ID & Password Provided")
run()
 