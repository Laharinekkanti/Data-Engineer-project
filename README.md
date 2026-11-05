# Movie Data Pipeline

## 1. Project Overview

This project is a Movie Data Pipeline developed using Python and SQLite. The main purpose of this project is to extract movie and rating data, clean and transform it, store it in a database, and perform SQL queries to analyse the data.

The project uses the MovieLens dataset and the OMDb API to collect additional movie information.

## 2. Project Objectives

The main objectives of this project are:

- To extract movie and rating data from CSV files.
- To clean and transform the data.
- To store the processed data in an SQLite database.
- To use the OMDb API to collect additional movie details.
- To perform SQL queries and analyse movie ratings, genres, directors, and release years.

## 3. Dataset Information

The project uses the MovieLens Small dataset.

The dataset contains:

| Dataset | Records |
|---|---:|
| Movies | 9,742 |
| Ratings | 100,836 |
| Genres | 19 |
| Movie-Genre Relationships | 22,050 |

Additional movie details were collected using the OMDb API. Currently, the database contains 839 records in the OMDb details table.

## 4. Technologies Used

- **Python:** Used to develop the ETL pipeline.
- **SQLite:** Used to store and manage the data.
- **SQL:** Used to query and analyse the data.
- **OMDb API:** Used to collect additional movie information.
- **CSV:** Used as the input data format.

## 5. Project Structure

```text
Movie_Data_Pipeline/
│
├── etl.py
├── schema.sql
├── queries.sql
├── README.md
├── movie_data.db
└── movie_data_small.db
```

The original CSV files are stored separately in the `data` folder.

## 6. ETL Process

The project follows three main steps:

### Extract

- Read movie information from `movies.csv`.
- Read rating information from `ratings.csv`.
- Collect additional movie details using the OMDb API when API access is enabled.

### Transform

- Clean movie titles.
- Extract release years from movie titles.
- Separate movie genres.
- Organise movie and rating information.
- Prepare the data before storing it in the database.

### Load

- Create database tables using SQLite.
- Store movie information.
- Store rating information.
- Store genre information and movie-genre relationships.
- Store the available OMDb details.

## 7. Database Design

The project uses SQLite to store the processed information.

The database contains the following tables:

- **movies:** Stores movie IDs, titles, and release years.
- **ratings:** Stores user ratings for movies.
- **genres:** Stores unique movie genres.
- **movie_genres:** Connects movies with their respective genres.
- **omdb_details:** Stores additional information collected from the OMDb API.

## 8. How to Run the Project

### Step 1: Install Python

Make sure Python is installed on your system.

### Step 2: Install the required package

```bash
pip install requests
```

SQLite is included with Python, so a separate installation is not required.

### Step 3: Run the ETL pipeline

To process the complete MovieLens dataset without making additional OMDb API requests:

```bash
python etl.py --skip-api
```

To process a limited number of movies for testing:

```bash
python etl.py --limit 100
```

To run the pipeline with OMDb API integration enabled, configure a valid OMDb API key and run:

```bash
python etl.py
```

## 9. SQL Analysis

After loading the data into SQLite, I used SQL queries to answer the following project questions.

### Question 1: Which movie has the highest average rating?

This query calculates the average rating for each movie and identifies the movie with the highest average rating.

```sql
SELECT
    m.movie_id,
    m.title,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM movies m
JOIN ratings r
    ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title
ORDER BY average_rating DESC
LIMIT 1;
```

### Question 2: What are the top 5 movie genres that have the highest average rating?

This query calculates the average rating for each genre and displays the top five genres.

```sql
SELECT
    g.genre_name,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM genres g
JOIN movie_genres mg
    ON g.genre_id = mg.genre_id
JOIN ratings r
    ON mg.movie_id = r.movie_id
GROUP BY g.genre_id, g.genre_name
ORDER BY average_rating DESC
LIMIT 5;
```

### Question 3: Who is the director with the most movies in this dataset?

This query counts the number of movies associated with each director using the available OMDb details.

```sql
SELECT
    director,
    COUNT(*) AS total_movies
FROM omdb_details
WHERE director IS NOT NULL
  AND director != ''
GROUP BY director
ORDER BY total_movies DESC
LIMIT 1;
```

**Note:** The director analysis is based on the available OMDb records. The database currently contains 839 OMDb detail records, so this result may not represent all 9,742 movies.

### Question 4: What is the average rating of movies released each year?

This query calculates the average movie rating for each release year.

```sql
SELECT
    m.release_year,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM movies m
JOIN ratings r
    ON m.movie_id = r.movie_id
WHERE m.release_year IS NOT NULL
GROUP BY m.release_year
ORDER BY m.release_year;
```

## 10. Database Verification

After running the ETL pipeline, I verified the database records.

The database contains:

| Table | Total Records |
|---|---:|
| movies | 9,742 |
| ratings | 100,836 |
| genres | 19 |
| movie_genres | 22,050 |
| omdb_details | 839 |

The ETL pipeline completed successfully, and the data was stored in the SQLite database.

## 11. Challenges and Limitations

- Handling movie titles and extracting release years.
- Separating movie genres and maintaining their relationships.
- Managing additional movie information through the OMDb API.
- OMDb API data is available only for a portion of the movies.
- The director analysis is limited to the available OMDb records.

## 12. Future Improvements

- Collect OMDb details for more movies.
- Add more data validation and cleaning steps.
- Create dashboards to visualise movie ratings and genre analysis.
- Schedule the ETL pipeline to run automatically.
- Integrate the pipeline with a cloud database.

## 13. Conclusion

Through this project, I developed a basic ETL pipeline using Python and SQLite. I extracted movie and rating data, performed data cleaning and transformation, and stored the processed information in a database.

I also used SQL queries to analyse movie ratings, identify highly rated genres, find directors with the most movies in the available OMDb data, and calculate average ratings by release year.

This project helped me understand the basic concepts of data engineering, ETL processes, database management, API integration, and SQL-based data analysis.