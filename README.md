# Introduction

This platform offers an authoring solution, simplifying the process of sharing academic content in various formats on the internet. This enhances the visibility of the work going on in an AI research collective or CDT, extending their audience reach. It was built using Django and Quarto, a scientific and technical authoring system (https://quarto.org). it is highly recommended to install (https://quarto.org/docs/get-started/) Quarto.org to render the application locally. 

The application permits users to generate posts concerning academic papers, append details related to conferences, and produce newsletters. Each of these content formats comes with its distinct publishing outcomes. These outcomes comprises visualization websites or generated documents. 

The visualization websites are applications built using Quarto authoring system, and are updated through push to their github repository and consequenty deployed via github actions. The types of publications that can be visualized in those applications are [academic publications](https://delmirodaladier.github.io/icr/) and [conferences](https://delmirodaladier.github.io/conference_calendar/). To illustrate, data from these categories are converted to the qmd format, commited to the apropriated repository and rendered in a correspondet Quarto application.

While the newsletter, the deliverable consists of a .doc document generated from the announcements inserted on the platform.


## Getting Started

Currently, the input application can be found [here](https://cdt-icr.onrender.com/). To start the authoring process, users are required to log in and then choose a section from the menu located in the upper right corner.

### Publishing a paper

The primary page is dedicated to authoring academic content. Information input can be achieved either by completing the form or by copying and pasting an Arxiv link of an article into the designated field.  

#### Publish using form

This serves as the standard method for publishing academic content using the application. Once logged in, users should complete the form on the homepage, ensuring all necessary fields are filled, and then proceed to submit the form. If the provided data is valid, the site will redirect to the success page, where a message containing the link to the recently created post will be accessible after a short interval.

#### Publish using Arxiv link

Alternatively, there exists a more direct approach to publishing. On the main page, users are presented with the choice of utilizing an Arxiv link for posting. By clicking on this option, the application will lead to the respective [page](https://cdt-icr.onrender.com/arxiv_post/). Following the pasting of the Arxiv link into the designated text field, the application employs a scraper to retrieve the requisite information. Subsequently, the site guides the user to a success page, where a message displaying the link to the recently crafted post will be accessible after a brief period.

### Conference Calendar

In this section, users have the option to input the conference information, thereby activating a web scraper that compiles data from the conference page and automatically populates the form. It's noteworthy to mention that the completion of the form can be done partially. 

### Newsletter

The newsletter comes into existence through a compilation of various announcements. In order to produce a single issue of the newsletter, users need to begin by creating multiple announcements.

#### Creating Announcements

To commence the creation of your newsletter, begin by generating a series of announcements. Follow these guidelines:

Begin by accessing the "Announcement" section. Subsequently, click on the "Create Announcement" button. Provide the essential information for your announcement, encompassing the title, content, and any relevant dates. Afterward, safeguard your announcement by utilizing the "Submit" button. If necessary, replicate these steps to generate additional announcements tailored to your newsletter's needs.

#### Creating Newsletter

Once you've completed the creation of your announcements, the next step is to proceed with crafting your newsletter. Here's how you can do it:

Navigate to the designated "Newsletter" section. There, you'll find the "Create Newsletter" button. You can proceed to provide the necessary information for your newsletter, including the title, description, and any other pertinent particulars. Alternatively, you can retain the default details.

From the available list of announcements, choose the ones you wish to incorporate into your newsletter. For each desired announcement, click on the "Preview" button. This will allow you to assess the content and layout of each announcement in the context of your newsletter.

Take a moment to review the overall content and arrangement of your newsletter, ensuring its visual appeal and coherence. Once satisfied, employ the "Submit" button to either save your newsletter or make any necessary edits. Additionally, on the preview page, you have the option to download the .doc file.

Congratulations are in order! You have now successfully generated your newsletter, complete with the selected announcements