<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ShlokVaidya/school-management-system">
    <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" fill="#ffffff" class="bi bi-backpack2" viewBox="0 0 16 16">
  <path d="M4.04 7.43a4 4 0 0 1 7.92 0 .5.5 0 1 1-.99.14 3 3 0 0 0-5.94 0 .5.5 0 1 1-.99-.14"/>
  <path fill-rule="evenodd" d="M4 9.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-7a.5.5 0 0 1-.5-.5zm1 .5v3h6v-3h-1v.5a.5.5 0 0 1-1 0V10z"/>
  <path d="M6 2.341V2a2 2 0 1 1 4 0v.341c2.33.824 4 3.047 4 5.659v1.191l1.17.585a1.5 1.5 0 0 1 .83 1.342V13.5a1.5 1.5 0 0 1-1.5 1.5h-1c-.456.607-1.182 1-2 1h-7a2.5 2.5 0 0 1-2-1h-1A1.5 1.5 0 0 1 0 13.5v-2.382a1.5 1.5 0 0 1 .83-1.342L2 9.191V8a6 6 0 0 1 4-5.659M7 2v.083a6 6 0 0 1 2 0V2a1 1 0 0 0-2 0M3 13.5A1.5 1.5 0 0 0 4.5 15h7a1.5 1.5 0 0 0 1.5-1.5V8A5 5 0 0 0 3 8zm-1-3.19-.724.362a.5.5 0 0 0-.276.447V13.5a.5.5 0 0 0 .5.5H2zm12 0V14h.5a.5.5 0 0 0 .5-.5v-2.382a.5.5 0 0 0-.276-.447L14 10.309Z"/>
</svg>
  </a>

<h3 align="center">School Management System</h3>

  <p align="center">
    A Flask and MySQL based school management system for managing students, teachers, sections, assignments, marks, attendance, announcements, and performance charts.
    <br />
    <a href="http://hackclub.com">View Demo</a>
    &middot;
    <a href="https://github.com/ShlokVaidya/school-management-system/issues/new?labels=bug">Report Bug</a>
    &middot;
    <a href="https://github.com/ShlokVaidya/school-management-system/issues/new?labels=enhancement">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

School Management System is a web application built for managing day-to-day academic records. It supports role-based dashboards for admins, teachers, and students, with tools for student records, teacher assignments, attendance, marks, announcements, and performance analysis.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [![Python][Python]][Python-url]
* [![Flask][Flask]][Flask-url]
* [![MySQL][MySQL]][MySQL-url]
* [![Jinja][Jinja]][Jinja-url]
* [![Chart.js][Chart.js]][Chart-url]
* [![HTML5][HTML5]][HTML5-url]
* [![Bootstrap][Bootstrap.com]][Bootstrap-url]
* [![JavaScript][JavaScript]][JavaScript-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

Follow these steps to run the project locally.

### Prerequisites

Make sure Python and MySQL are installed on your system.
* Python packages
  ```sh
  pip install flask mysql-connector-python
  ```

### Installation

1. Create the MySQL database
   ```sh
   mysql -u root -p < database_setup.sql
   ```
2. Clone the repo
   ```sh
   git clone https://github.com/ShlokVaidya/school-management-system.git
   ```
3. Open the project folder
   ```sh
   cd school-management-system
   ```
4. Update your MySQL settings in `config.py`
   ```py
   MYSQL_HOST = 'localhost'
   MYSQL_USER = 'root'
   MYSQL_PASSWORD = 'your_password'
   MYSQL_DB = 'student_tracker'
   ```
5. Run the Flask app
   ```sh
   python app.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [x] Student and teacher management
- [x] Assignment, marks, and attendance tracking
- [x] Role-based dashboards
    - [ ] More reporting and export options

See the [open issues](https://github.com/ShlokVaidya/school-management-system/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors:

<a href="https://github.com/ShlokVaidya/school-management-system/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ShlokVaidya/school-management-system" alt="contrib.rocks image" />
</a>

---
<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/ShlokVaidya/school-management-system.svg?style=for-the-badge
[contributors-url]: https://github.com/ShlokVaidya/school-management-system/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/ShlokVaidya/school-management-system.svg?style
[forks-url]: https://github.com/ShlokVaidya/school-management-system/network/members
[stars-shield]: https://img.shields.io/github/stars/ShlokVaidya/school-management-system.svg?style=for-the-badge
[stars-url]: https://github.com/ShlokVaidya/school-management-system/stargazers
[issues-shield]: https://img.shields.io/github/issues/ShlokVaidya/school-management-system.svg?style=for-the-badge
[issues-url]: https://github.com/ShlokVaidya/school-management-system/issues
[license-shield]: https://img.shields.io/github/license/ShlokVaidya/school-management-system.svg?style=for-the-badge
[license-url]: https://github.com/ShlokVaidya/school-management-system/blob/main/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://github.com/ShlokVaidya
[product-screenshot]: public/school-bag.png
<!-- Shields.io badges. You can a comprehensive list with many more badges at: https://github.com/inttter/md-badges -->
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Flask]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[Flask-url]: https://flask.palletsprojects.com/
[MySQL]: https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white
[MySQL-url]: https://www.mysql.com/
[Jinja]: https://img.shields.io/badge/Jinja-B41717?style=for-the-badge&logo=jinja&logoColor=white
[Jinja-url]: https://jinja.palletsprojects.com/
[Chart.js]: https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white
[Chart-url]: https://www.chartjs.org/
[HTML5]: https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white
[HTML5-url]: https://developer.mozilla.org/en-US/docs/Web/HTML
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JavaScript]: https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black
[JavaScript-url]: https://developer.mozilla.org/en-US/docs/Web/JavaScript
